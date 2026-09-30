        .setcpu "6502"

VIA1_ORB     = $7f20
VIA1_DDRB    = $7f22
VIA2_ORB     = $7f40
VIA2_IRA     = $7f41
VIA2_DDRB    = $7f42
VIA2_DDRA    = $7f43
SID_FREQ_L   = $7f60
SID_FREQ_H   = $7f61
SID_CTRL     = $7f64
SID_AD       = $7f65
SID_SR       = $7f66
SID_VOLUME   = $7f78

GATE_ON  = %00100001            ; sawtooth, gate on: the tone starts
GATE_OFF = %00100000            ; sawtooth, gate off: the tone dies away

        .zeropage
tmp:    .res 1
code:   .res 1                  ; code of the pressed key

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
        jsr keys_init
        lda #$09                ; attack 0, decay 9
        sta SID_AD
        lda #$8a                ; sustain 8, release 10
        sta SID_SR
        lda #$0f                ; full volume
        sta SID_VOLUME
loop:   jsr keys_update
        ldx #0
@find:  lda note_keys,x         ; look the key up in the table
        cmp #$ff
        beq @silent
        cmp code
        beq @play
        inx
        bne @find
@play:  lda note_lo,x           ; set the frequency and start the tone
        sta SID_FREQ_L
        lda note_hi,x
        sta SID_FREQ_H
        lda #GATE_ON
        sta SID_CTRL
        jmp loop
@silent:
        lda #GATE_OFF           ; no note pressed: let the tone die away
        sta SID_CTRL
        jmp loop

; keys (scancodes) and the frequency values of the notes C to D5
note_keys: .byte 1, 67, 65, 11, 9, 17, 23, 21, 31, 29, 27, 25, 33, 83, 81, 43, $ff
note_lo:   .byte $25, $2a, $3f, $64, $9a, $e3, $3f, $b1, $38, $d6, $8d, $5e, $4b, $55, $7e, $c8
note_hi:   .byte $11, $12, $13, $14, $15, $16, $18, $19, $1b, $1c, $1e, $20, $22, $24, $26, $28

; keyboard routines as in chapter 10
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
