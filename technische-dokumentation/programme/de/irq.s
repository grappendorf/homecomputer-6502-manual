        .setcpu "6502"

VIA1_ORA  = $7f21
VIA1_DDRA = $7f23
VIA1_T1CL = $7f24
VIA1_T1CH = $7f25
VIA1_ACR  = $7f2b
VIA1_IER  = $7f2e

LED            = %10000000
TIMER_INTERVAL = 10000          ; ein Interrupt alle 100 ms (bei 1 MHz)

        .zeropage
ticks:      .res 1              ; gezählte Interrupts
max_ticks:  .res 1              ; so viele Interrupts bis zum Wechsel der LED

        .segment "VECTORS"
        .word   nmi
        .word   reset
        .word   irq

        .code
reset:  jmp main
nmi:    jmp nmi_handler
irq:    jmp irq_handler

main:   sei                     ; Interrupts sperren, bis alles eingerichtet ist
        cld
        ldx #$ff
        txs
        lda VIA1_DDRA           ; PA7 (die LED) als Ausgang, LED aus
        ora #LED
        sta VIA1_DDRA
        lda VIA1_ORA
        and #<~LED
        sta VIA1_ORA
        lda #0
        sta ticks
        lda #100                ; 100 mal 100 ms: LED wechselt jede Sekunde
        sta max_ticks
        lda #%01000000          ; Timer 1 läuft ständig, PB7 bleibt frei
        sta VIA1_ACR
        lda #%11000000          ; Interrupt von Timer 1 freigeben
        sta VIA1_IER
        lda #<TIMER_INTERVAL    ; Zähler laden: erst niedriges, dann hohes Byte
        sta VIA1_T1CL
        lda #>TIMER_INTERVAL
        sta VIA1_T1CH
        cli                     ; Interrupts freigeben
loop:   jmp loop                ; das Hauptprogramm hat nichts zu tun

; NMI: ab jetzt wechselt die LED zehnmal schneller
nmi_handler:
        pha
        lda #10                 ; 10 mal 100 ms: LED wechselt jede Zehntelsekunde
        sta max_ticks
        pla
        rti

; IRQ: alle 100 ms
irq_handler:
        pha
        lda VIA1_T1CL           ; Lesen von T1C-L löscht die Interrupt-Anforderung
        inc ticks
        lda ticks
        cmp max_ticks
        bcc @done
        lda #0
        sta ticks
        lda VIA1_ORA
        eor #LED                ; LED umschalten
        sta VIA1_ORA
@done:  pla
        rti
