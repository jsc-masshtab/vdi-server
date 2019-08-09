import { OnInit, ElementRef, Renderer, Input, Directive } from '@angular/core';

@Directive({ selector: '[focusMe]' })

export class FocusMeDirective implements OnInit {

    @Input('focusMe') isFocused: boolean;

    constructor(private hostElement: ElementRef, private renderer: Renderer) {}

    ngOnInit() {
        this.focus();
    }

    private focus() {
        if (this.isFocused) {
            this.renderer.invokeElementMethod(this.hostElement.nativeElement, 'focus');
        }
    }
}