        .setcpu "6502"

VIA_ORA  = $7f21
VIA_DDRA = $7f23

LCD_RS = %00010000              ; Register Select: Befehl (0) oder Zeichen (1)
LCD_E1 = %00100000              ; Enable des oberen Controllers (Zeilen 1, 2)
LCD_E2 = %01000000              ; Enable des unteren Controllers (Zeilen 3, 4)

        .zeropage
ptr:    .res 2
lcd_e:  .res 1                  ; gerade gewählter Controller
led:    .res 1                  ; Zustand der LED an PA7 (Bit 7)
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
        ldx #0                  ; Spalte 0
        ldy #1                  ; Zeile 1 (die zweite)
        jsr lcd_goto
        lda #'>'
        jsr lcd_putc
        jsr lcd_cursor_blink
        jsr led_on              ; LED an
        ldx #0
        ldy #2                  ; Zeile 2 (die dritte)
        jsr lcd_goto
        lda #<msg_second
        ldx #>msg_second
        jsr lcd_puts
halt:   jmp halt

; Display initialisieren (4-Bit-Betrieb, beide Controller)
lcd_init:
        lda #$ff                ; alle Leitungen von Port A sind Ausgänge
        sta VIA_DDRA
        lda led
        sta VIA_ORA
        ldx #40                 ; 40 ms nach dem Einschalten warten
        jsr delay_ms
        lda #LCD_E1 | LCD_E2    ; beide Controller ansprechen
        sta lcd_e
        lda #3                  ; dreimal $3: 8-Bit-Betrieb sicherstellen
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
        lda #2                  ; dann $2: auf 4-Bit-Betrieb umschalten
        jsr lcd_write4
        ldx #1
        jsr delay_ms
        lda #%00101000          ; 4 Bit, zwei Zeilen, 5×8 Punkte
        jsr lcd_cmd
        lda #%00001000          ; Anzeige aus
        jsr lcd_cmd
        jsr lcd_clear
        lda #%00000110          ; Cursor läuft nach rechts
        jsr lcd_cmd
        lda #%00001100          ; Anzeige an, Cursor aus
        jsr lcd_cmd
        lda #LCD_E1             ; ab jetzt oberen Controller wählen
        sta lcd_e
        rts

; A = RS und Nibble: Daten setzen, E kurz High (RS und Daten bleiben stehen)
lcd_write4:
        and #$1f
        ora led                 ; die LED (PA7) bleibt bei jedem Schreiben erhalten
        sta tmp
        sta VIA_ORA
        ora lcd_e
        sta VIA_ORA
        lda tmp
        sta VIA_ORA
        rts

; A = Befehl (RS = 0): zuerst oberes, dann unteres Nibble
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
        ldx #10                 ; etwa 50 µs warten
@wait:  dex
        bne @wait
        rts

lcd_clear:
        lda #%00000001
        jmp lcd_cmd

lcd_cursor_blink:
        lda #%00001111
        jmp lcd_cmd

; X = Spalte, Y = Zeile (0 bis 3)
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
        adc #$40                ; zweite Zeile beginnt bei Adresse $40
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

; X Millisekunden warten (bei 1 MHz, je Millisekunde 1001 Takte)
delay_ms:
@ms:    ldy #199
@us:    dey
        bne @us
        dex
        bne @ms
        rts

; LED ein- und ausschalten: PA7 teilt sich Port A mit dem Display
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
