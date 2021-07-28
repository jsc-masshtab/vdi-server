import { OnInit, ElementRef, Input, Directive } from '@angular/core';

@Directive({ selector: '[focusMe]' })

export class FocusMeDirective implements OnInit {

    @Input('focusMe') isFocused: boolean;

    constructor(private hostElement: ElementRef) {}

    ngOnInit() {
        this.focus();
    }

    private focus() {
        if (this.isFocused) {
            this.hostElement.nativeElement.focus();
        }
    }
}
