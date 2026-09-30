        .setcpu "6502"

VIA_ORA  = $7f21
VIA_DDRA = $7f23

LCD_RS = %00010000              ; register select: command (0) or character (1)
LCD_E1 = %00100000              ; enable of the upper controller (rows 1, 2)
LCD_E2 = %01000000              ; enable of the lower controller (rows 3, 4)

        .zeropage
ptr:    .res 2
lcd_e:  .res 1                  ; currently selected controller
led:    .res 1                  ; state of the LED at PA7 (bit 7)
tmp:    .res 1

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
        jsr lcd_init
        lda #<msg_welcome
        ldx #>msg_welcome
        jsr lcd_puts
        ldx #0                  ; column 0
        ldy #1                  ; row 1 (the second)
        jsr lcd_goto
        lda #'>'
        jsr lcd_putc
        jsr lcd_cursor_blink
        jsr led_on              ; LED on
        ldx #0
        ldy #2                  ; row 2 (the third)
        jsr lcd_goto
        lda #<msg_second
        ldx #>msg_second
        jsr lcd_puts
halt:   jmp halt

; initialize the display (4-bit mode, both controllers)
lcd_init:
        lda #$ff                ; all lines of port A are outputs
        sta VIA_DDRA
        lda led
        sta VIA_ORA
        ldx #40                 ; wait 40 ms after power-on
        jsr delay_ms
        lda #LCD_E1 | LCD_E2    ; address both controllers
        sta lcd_e
        lda #3                  ; $3 three times: make sure of 8-bit mode
        jsr lcd_write4
        ldx #5
        jsr delay_ms
        lda #3
        jsr lcd_write4
        ldx #1
        jsr delay_ms
        lda #3
        jsr lcd_write4
        ldx #1
        jsr delay_ms
        lda #2                  ; then $2: switch to 4-bit mode
        jsr lcd_write4
        ldx #1
        jsr delay_ms
        lda #%00101000          ; 4 bit, two lines, 5×8 dots
        jsr lcd_cmd
        lda #%00001000          ; display off
        jsr lcd_cmd
        jsr lcd_clear
        lda #%00000110          ; cursor moves to the right
        jsr lcd_cmd
        lda #%00001100          ; display on, cursor off
        jsr lcd_cmd
        lda #LCD_E1             ; from now on select the upper controller
        sta lcd_e
        rts

; A = RS and nibble: set data, pulse E high (RS and data stay)
lcd_write4:
        and #$1f
        ora led                 ; the LED (PA7) is kept at every write
        sta tmp
        sta VIA_ORA
        ora lcd_e
        sta VIA_ORA
        lda tmp
        sta VIA_ORA
        rts

; A = command (RS = 0): high nibble first, then low nibble
lcd_cmd:
        pha
        lsr
        lsr
        lsr
        lsr
        jsr lcd_write4
        pla
        and #$0f
        jsr lcd_write4
        ldx #2
        jmp delay_ms

lcd_putc:
        pha
        lsr
        lsr
        lsr
        lsr
        ora #LCD_RS
        jsr lcd_write4
        pla
        and #$0f
        ora #LCD_RS
        jsr lcd_write4
        ldx #10                 ; wait about 50 µs
@wait:  dex
        bne @wait
        rts

lcd_clear:
        lda #%00000001
        jmp lcd_cmd

lcd_cursor_blink:
        lda #%00001111
        jmp lcd_cmd

; X = column, Y = row (0 to 3)
lcd_goto:
        cpy #2
        bcs @lower
        lda #LCD_E1
        bne @set
@lower: lda #LCD_E2
        dey
        dey
@set:   sta lcd_e
        txa
        cpy #0
        beq @cmd
        clc
        adc #$40                ; second line starts at address $40
@cmd:   ora #$80
        jmp lcd_cmd

lcd_puts:
        sta ptr
        stx ptr+1
        ldy #0
@loop:  lda (ptr),y
        beq @done
        jsr lcd_putc
        iny
        bne @loop
@done:  rts

; wait X milliseconds (at 1 MHz, 1001 clocks per millisecond)
delay_ms:
@ms:    ldy #199
@us:    dey
        bne @us
        dex
        bne @ms
        rts

; switch the LED on and off: PA7 shares port A with the display
led_on: lda #$80
        sta led
        sta VIA_ORA
        rts

led_off:
        lda #0
        sta led
        sta VIA_ORA
        rts

msg_welcome: .byte "Welcome to the 6502 HomeComputer!", $00
msg_second:  .byte "This is line 3.", $00
