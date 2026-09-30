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

GATE_ON  = %00100001            ; Sägezahn, Gate an: Ton beginnt
GATE_OFF = %00100000            ; Sägezahn, Gate aus: Ton klingt aus

        .zeropage
tmp:    .res 1
code:   .res 1                  ; Code der gedrückten Taste

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
        lda #$09                ; Attack 0, Decay 9
        sta SID_AD
        lda #$8a                ; Sustain 8, Release 10
        sta SID_SR
        lda #$0f                ; volle Lautstärke
        sta SID_VOLUME
loop:   jsr keys_update
        ldx #0
@find:  lda note_keys,x         ; Taste in der Tabelle suchen
        cmp #$ff
        beq @silent
        cmp code
        beq @play
        inx
        bne @find
@play:  lda note_lo,x           ; Frequenz setzen und Ton starten
        sta SID_FREQ_L
        lda note_hi,x
        sta SID_FREQ_H
        lda #GATE_ON
        sta SID_CTRL
        jmp loop
@silent:
        lda #GATE_OFF           ; keine Note gedrückt: Ton ausklingen lassen
        sta SID_CTRL
        jmp loop

; Tasten (Scancodes) und die Frequenzwerte der Töne C bis D5
note_keys: .byte 1, 67, 65, 11, 9, 17, 23, 21, 31, 29, 27, 25, 33, 83, 81, 43, $ff
note_lo:   .byte $25, $2a, $3f, $64, $9a, $e3, $3f, $b1, $38, $d6, $8d, $5e, $4b, $55, $7e, $c8
note_hi:   .byte $11, $12, $13, $14, $15, $16, $18, $19, $1b, $1c, $1e, $20, $22, $24, $26, $28

; Tastaturroutinen wie in Kapitel 10
keys_init:
        lda #$ff
        sta VIA2_DDRB           ; VIA2 Port B: Zeilen 0 bis 7 als Ausgang
        lda #$00
        sta VIA2_DDRA           ; VIA2 Port A: Spalten 0 bis 7 als Eingang
        lda VIA1_DDRB
        ora #$3f                ; VIA1 PB0 bis PB5: Zeilen 8 bis 13 als Ausgang
        sta VIA1_DDRB
        jmp rows_idle

; alle Zeilen auf High
rows_idle:
        lda #$ff
        sta VIA2_ORB
        lda VIA1_ORB
        ora #$3f
        sta VIA1_ORB
        rts

; X = Zeile (0 bis 13): nur diese Zeile auf Low
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

; Tastatur abtasten: A = Scancode oder $FF
keys_scan:
        ldx #0
@row:   jsr select_row
        lda VIA2_IRA
        eor #$ff                ; gedrückt = Bit gesetzt
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
@done:  sty tmp                 ; Y = Spalte
        txa
        asl
        asl
        asl
        ora tmp                 ; Zeile * 8 + Spalte
        pha
        jsr rows_idle
        pla
        rts

; Abtasten mit Entprellen: Code in code
keys_update:
        jsr keys_scan
        cmp #$ff
        beq @none
        sta code
        ldx #10                 ; 10 ms warten und noch einmal abtasten
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
