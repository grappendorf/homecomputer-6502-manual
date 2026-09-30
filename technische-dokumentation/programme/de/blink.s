        .setcpu "6502"

VIA_ORB  = $7f20
VIA_DDRB = $7f22

        .segment "VECTORS"
        .word   nmi
        .word   reset
        .word   irq

        .code
reset:  jmp main
nmi:    rti
irq:    rti

main:   lda #$ff                ; alle Leitungen von Port B als Ausgang
        sta VIA_DDRB
loop:   lda #$00                ; LED aus
        sta VIA_ORB
        jsr delay
        lda #$ff                ; LED an
        sta VIA_ORB
        jsr delay
        jmp loop

delay:  ldx #200                ; Warteschleife: 200 × 256 Durchläufe, etwa eine Viertelsekunde
@outer: ldy #0
@inner: dey
        bne @inner
        dex
        bne @outer
        rts
