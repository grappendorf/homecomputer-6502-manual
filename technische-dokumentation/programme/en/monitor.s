        .setcpu "6502"

ACIA_DATA    = $7f00
ACIA_STATUS  = $7f01
ACIA_COMMAND = $7f02
ACIA_CONTROL = $7f03

BUFLEN = 80

        .zeropage
ptr:    .res 2                  ; pointer for strings and memory access
val:    .res 2                  ; value from parse_hex
tmp:    .res 1                  ; scratch variable

        .bss
buffer: .res BUFLEN + 1         ; input line

        .segment "VECTORS"
        .word   nmi
        .word   reset
        .word   irq

        .code
reset:  jmp main
nmi:    rti
irq:    rti

main:   cld
        ldx #$ff                ; initialize the stack
        txs
        jsr acia_init
        lda #<msg_welcome
        ldx #>msg_welcome
        jsr puts

loop:   lda #<prompt
        ldx #>prompt
        jsr puts
        jsr gets                ; read a line
        lda buffer
        beq loop                ; empty line: do nothing
        cmp #'m'
        bne @check_w
        jsr cmd_memory
        jmp loop
@check_w:
        cmp #'w'
        bne @check_j
        jsr cmd_write
        jmp loop
@check_j:
        cmp #'j'
        bne @unknown
        jsr cmd_jump
        jmp loop
@unknown:
        jsr error
        jmp loop

; print an error message
error:  lda #<msg_unknown
        ldx #>msg_unknown
        jmp puts

; m <address>: show 16 bytes
cmd_memory:
        ldy #1
        jsr parse_hex
        bcs @error
        lda val
        sta ptr
        lda val+1
        sta ptr+1
        lda ptr+1               ; print the address
        jsr puthex
        lda ptr
        jsr puthex
        jsr space
        jsr space
        ldy #0
@hex:   lda (ptr),y
        jsr puthex
        jsr space
        cpy #7
        bne @next
        jsr space               ; gap between the two halves
@next:  iny
        cpy #16
        bne @hex
        jsr space
        jsr space
        lda #'|'
        jsr putc
        ldy #0
@ascii: lda (ptr),y
        cmp #' '
        bcc @dot                ; printable characters only, else a dot
        cmp #$7f
        bcc @put
@dot:   lda #'.'
@put:   jsr putc
        iny
        cpy #16
        bne @ascii
        lda #'|'
        jsr putc
        jmp newline
@error: jmp error

; w <address> <byte>: write a byte
cmd_write:
        ldy #1
        jsr parse_hex
        bcs @error
        lda val
        sta ptr
        lda val+1
        sta ptr+1
        jsr parse_hex           ; second value: the byte
        bcs @error
        lda val
        ldy #0
        sta (ptr),y             ; store the byte
        lda ptr+1
        jsr puthex
        lda ptr
        jsr puthex
        lda #':'
        jsr putc
        lda (ptr),y             ; read back for checking
        jsr puthex
        jmp newline
@error: jmp error

; j <address>: call a program, RTS returns
cmd_jump:
        ldy #1
        jsr parse_hex
        bcs @error
        jsr call
        rts
@error: jmp error
call:   jmp (val)               ; JSR to here, JMP to the target: its RTS returns to cmd_jump

; Reads a hex number from position Y of the input into val. Carry set: no number.
parse_hex:
        lda #0
        sta val
        sta val+1
@skip:  lda buffer,y
        cmp #' '
        bne @first
        iny
        bne @skip
@first: jsr hexdigit
        bcs @none
@digit: sta tmp
        asl val                 ; val = val * 16
        rol val+1
        asl val
        rol val+1
        asl val
        rol val+1
        asl val
        rol val+1
        lda val
        ora tmp
        sta val
        iny
        lda buffer,y
        jsr hexdigit
        bcc @digit
        clc
        rts
@none:  sec
        rts

; A = character -> A = value 0..15, carry set: not a hex digit
hexdigit:
        cmp #'0'
        bcc @no
        cmp #'9' + 1
        bcc @decimal
        ora #$20                ; convert to lower case
        cmp #'a'
        bcc @no
        cmp #'f' + 1
        bcs @no
        sec
        sbc #'a' - 10
        clc
        rts
@decimal:
        sec
        sbc #'0'
        clc
        rts
@no:    sec
        rts

; print A as two hex digits
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
        adc #'A' - 10 - 1       ; carry is set: +1
        jmp putc
@digit: ora #'0'
        jmp putc

space:  lda #' '
        jmp putc

newline:
        lda #$0d
        jsr putc
        lda #$0a
        jmp putc

; print text, address in A (low) and X (high)
puts:   sta ptr
        stx ptr+1
        ldy #0
@loop:  lda (ptr),y
        beq @done
        jsr putc
        iny
        bne @loop
@done:  rts

; read a line into buffer, backspace allowed
gets:   ldx #0
@loop:  jsr getc
        cmp #$0d
        beq @done
        cmp #$08
        beq @back
        cmp #$7f
        beq @back
        cmp #' '
        bcc @loop               ; ignore control characters
        cpx #BUFLEN
        bcs @loop
        sta buffer,x
        inx
        jsr putc                ; echo the character
        jmp @loop
@back:  cpx #0
        beq @loop
        dex
        lda #$08
        jsr putc
        lda #' '
        jsr putc
        lda #$08
        jsr putc
        jmp @loop
@done:  lda #0
        sta buffer,x
        jmp newline

; ACIA: output and input of one character
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

getc:   lda ACIA_STATUS
        and #$08
        beq getc
        lda ACIA_DATA
        rts

prompt:      .byte "> ", $00
msg_welcome: .byte $0d, $0a, "Welcome to the 6502 monitor program!", $0d, $0a, $00
msg_unknown: .byte "Unknown command", $0d, $0a, $00
