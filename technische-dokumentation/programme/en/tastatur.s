        .setcpu "6502"

ACIA_DATA    = $7f00
ACIA_STATUS  = $7f01
ACIA_COMMAND = $7f02
ACIA_CONTROL = $7f03
VIA1_ORB     = $7f20
VIA1_DDRB    = $7f22
VIA2_ORB     = $7f40
VIA2_IRA     = $7f41
VIA2_DDRB    = $7f42
VIA2_DDRA    = $7f43

        .zeropage
ptr:    .res 2
tmp:    .res 1
code:   .res 1                  ; code of the pressed key ($FF = none)
last:   .res 1                  ; last code reported

        .segment "VECTORS"
        .word   nmi
        .word   reset
        .word   irq

        .code
reset:  jmp main
nmi:    rti
irq:    rti

main:   cld
        ldx #$ff
        txs
        jsr acia_init
        jsr keys_init
        lda #$ff
        sta last
loop:   jsr keys_update
        lda code
        cmp last                ; report changes only
        beq loop
        sta last
        cmp #$ff
        beq loop                ; releasing is not reported
        lda #<msg_key
        ldx #>msg_key
        jsr puts
        lda code
        jsr puthex
        jsr newline
        jmp loop

; set up the ports: rows output, columns input
keys_init:
        lda #$ff
        sta VIA2_DDRB           ; VIA2 port B: rows 0 to 7 as outputs
        lda #$00
        sta VIA2_DDRA           ; VIA2 port A: columns 0 to 7 as inputs
        lda VIA1_DDRB
        ora #$3f                ; VIA1 PB0 to PB5: rows 8 to 13 as outputs
        sta VIA1_DDRB
        jmp rows_idle

; all rows high
rows_idle:
        lda #$ff
        sta VIA2_ORB
        lda VIA1_ORB
        ora #$3f
        sta VIA1_ORB
        rts

; X = row (0 to 13): only this row low
select_row:
        jsr rows_idle
        cpx #8
        bcs @via1
        lda row_mask,x
        sta VIA2_ORB
        rts
@via1:  lda row_mask - 8,x
        and VIA1_ORB
        sta VIA1_ORB
        rts

row_mask: .byte $fe, $fd, $fb, $f7, $ef, $df, $bf, $7f

; scan the keyboard: A = scancode or $FF
keys_scan:
        ldx #0
@row:   jsr select_row
        lda VIA2_IRA
        eor #$ff                ; pressed = bit set
        bne @found
        inx
        cpx #14
        bne @row
        jsr rows_idle
        lda #$ff
        rts
@found: ldy #0
@bit:   lsr
        bcs @done
        iny
        bne @bit
@done:  sty tmp                 ; Y = column
        txa
        asl
        asl
        asl
        ora tmp                 ; row * 8 + column
        pha
        jsr rows_idle
        pla
        rts

; scan with debouncing: code in code
keys_update:
        jsr keys_scan
        cmp #$ff
        beq @none
        sta code
        ldx #10                 ; wait 10 ms and scan again
        jsr delay_ms
        jsr keys_scan
        cmp code
        beq @done
@none:  lda #$ff
        sta code
@done:  rts

delay_ms:
@ms:    ldy #199
@us:    dey
        bne @us
        dex
        bne @ms
        rts

; output through the ACIA as in the monitor program
acia_init:
        lda #%00001011
        sta ACIA_COMMAND
        lda #%00011111
        sta ACIA_CONTROL
        rts

putc:   pha
@wait:  lda ACIA_STATUS
        and #$10
        beq @wait
        pla
        sta ACIA_DATA
        rts

puts:   sta ptr
        stx ptr+1
        ldy #0
@loop:  lda (ptr),y
        beq @done
        jsr putc
        iny
        bne @loop
@done:  rts

puthex: pha
        lsr
        lsr
        lsr
        lsr
        jsr @nibble
        pla
        and #$0f
@nibble:
        cmp #10
        bcc @digit
        adc #'A' - 10 - 1
        jmp putc
@digit: ora #'0'
        jmp putc

newline:
        lda #$0d
        jsr putc
        lda #$0a
        jmp putc

msg_key: .byte "Scancode: $", $00
