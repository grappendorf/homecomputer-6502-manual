        .setcpu "6502"

VIA1_ORA  = $7f21
VIA1_DDRA = $7f23
VIA1_T1CL = $7f24
VIA1_T1CH = $7f25
VIA1_ACR  = $7f2b
VIA1_IER  = $7f2e

LED            = %10000000
TIMER_INTERVAL = 10000          ; one interrupt every 100 ms (at 1 MHz)

        .zeropage
ticks:      .res 1              ; interrupts counted
max_ticks:  .res 1              ; number of interrupts until the LED changes

        .segment "VECTORS"
        .word   nmi
        .word   reset
        .word   irq

        .code
reset:  jmp main
nmi:    jmp nmi_handler
irq:    jmp irq_handler

main:   sei                     ; block interrupts until everything is set up
        cld
        ldx #$ff
        txs
        lda VIA1_DDRA           ; PA7 (the LED) as output, LED off
        ora #LED
        sta VIA1_DDRA
        lda VIA1_ORA
        and #<~LED
        sta VIA1_ORA
        lda #0
        sta ticks
        lda #100                ; 100 times 100 ms: the LED changes every second
        sta max_ticks
        lda #%01000000          ; timer 1 runs continuously, PB7 stays free
        sta VIA1_ACR
        lda #%11000000          ; enable the timer 1 interrupt
        sta VIA1_IER
        lda #<TIMER_INTERVAL    ; load the counter: low byte first, then high byte
        sta VIA1_T1CL
        lda #>TIMER_INTERVAL
        sta VIA1_T1CH
        cli                     ; enable interrupts
loop:   jmp loop                ; the main program has nothing to do

; NMI: from now on the LED changes ten times faster
nmi_handler:
        pha
        lda #10                 ; 10 times 100 ms: the LED changes every tenth of a second
        sta max_ticks
        pla
        rti

; IRQ: every 100 ms
irq_handler:
        pha
        lda VIA1_T1CL           ; reading T1C-L clears the interrupt request
        inc ticks
        lda ticks
        cmp max_ticks
        bcc @done
        lda #0
        sta ticks
        lda VIA1_ORA
        eor #LED                ; toggle the LED
        sta VIA1_ORA
@done:  pla
        rti
