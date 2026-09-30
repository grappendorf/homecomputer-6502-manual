        .setcpu "6502"

ACIA_DATA    = $7f00
ACIA_STATUS  = $7f01
ACIA_COMMAND = $7f02
ACIA_CONTROL = $7f03

BUFLEN = 80

        .zeropage
ptr:    .res 2                  ; Zeiger für Texte und Speicherzugriffe
val:    .res 2                  ; Wert aus parse_hex
tmp:    .res 1                  ; Hilfsvariable

        .bss
buffer: .res BUFLEN + 1         ; Eingabezeile

        .segment "VECTORS"
        .word   nmi
        .word   reset
        .word   irq

        .code
reset:  jmp main
nmi:    rti
irq:    rti

main:   cld
        ldx #$ff                ; Stapel initialisieren
        txs
        jsr acia_init
        lda #<msg_welcome
        ldx #>msg_welcome
        jsr puts

loop:   lda #<prompt
        ldx #>prompt
        jsr puts
        jsr gets                ; Zeile einlesen
        lda buffer
        beq loop                ; leere Zeile: nichts tun
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

; Fehlermeldung ausgeben
error:  lda #<msg_unknown
        ldx #>msg_unknown
        jmp puts

; m <Adresse>: 16 Bytes anzeigen
cmd_memory:
        ldy #1
        jsr parse_hex
        bcs @error
        lda val
        sta ptr
        lda val+1
        sta ptr+1
        lda ptr+1               ; Adresse ausgeben
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
        jsr space               ; Lücke zwischen den beiden Hälften
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
        bcc @dot                ; nur druckbare Zeichen, sonst Punkt
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

; w <Adresse> <Byte>: Byte schreiben
cmd_write:
        ldy #1
        jsr parse_hex
        bcs @error
        lda val
        sta ptr
        lda val+1
        sta ptr+1
        jsr parse_hex           ; zweiter Wert: das Byte
        bcs @error
        lda val
        ldy #0
        sta (ptr),y             ; Byte speichern
        lda ptr+1
        jsr puthex
        lda ptr
        jsr puthex
        lda #':'
        jsr putc
        lda (ptr),y             ; zur Kontrolle zurücklesen
        jsr puthex
        jmp newline
@error: jmp error

; j <Adresse>: Programm aufrufen, RTS kehrt zurück
cmd_jump:
        ldy #1
        jsr parse_hex
        bcs @error
        jsr call
        rts
@error: jmp error
call:   jmp (val)               ; JSR hierher, JMP zum Ziel: RTS des Ziels kehrt zu cmd_jump zurück

; Liest eine Hexzahl ab Position Y der Eingabe nach val. Carry gesetzt: keine Zahl.
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

; A = Zeichen -> A = Wert 0..15, Carry gesetzt: keine Hexziffer
hexdigit:
        cmp #'0'
        bcc @no
        cmp #'9' + 1
        bcc @decimal
        ora #$20                ; in Kleinbuchstaben wandeln
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

; A als zwei Hexziffern ausgeben
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
        adc #'A' - 10 - 1       ; Carry ist gesetzt: +1
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

; Text ausgeben, Adresse in A (niedrig) und X (hoch)
puts:   sta ptr
        stx ptr+1
        ldy #0
@loop:  lda (ptr),y
        beq @done
        jsr putc
        iny
        bne @loop
@done:  rts

; Zeile in buffer lesen, Rücktaste erlaubt
gets:   ldx #0
@loop:  jsr getc
        cmp #$0d
        beq @done
        cmp #$08
        beq @back
        cmp #$7f
        beq @back
        cmp #' '
        bcc @loop               ; Steuerzeichen ignorieren
        cpx #BUFLEN
        bcs @loop
        sta buffer,x
        inx
        jsr putc                ; Zeichen zurücksenden
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

; ACIA: Ausgabe und Eingabe eines Zeichens
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
