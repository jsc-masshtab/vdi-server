/* tslint:disable:directive-class-suffix */
/* eslint-disable @angular-eslint/directive-class-suffix */
import { HostListener, ElementRef, Directive } from '@angular/core';

@Directive()
export class DetailsMove  {

  public pageHeightMinNumber: number = 315;
  public pageHeightMin: string = '315px';
  public pageHeightMax: string = '100%';
  public pageHeight: string = '100%';
  public pageRollup: boolean = false;
  public pageShow: boolean = false
  public timeout: any;
  

  constructor() {}

  @HostListener('window:resize', ['$event']) onResize(view: ElementRef) {
    if (this.timeout) {
      clearTimeout(this.timeout);
    }
    this.timeout = setTimeout(() => {
      if (this.pageHeight === this.pageHeightMin) {
        if ((view.nativeElement.clientHeight - this.pageHeightMinNumber) < (this.pageHeightMinNumber + 250)) {
          this.pageRollup = true;
        } else {
          this.pageRollup = false;
        }
      }
    }, 500);
  }

  public componentActivate(view: ElementRef): void {
    this.pageHeight = this.pageHeightMin;

    if ((view.nativeElement.clientHeight - this.pageHeightMinNumber) < (this.pageHeightMinNumber + 250)) {
      this.pageRollup = true;
    }
  }

  public componentDeactivate(): void {
    this.pageHeight = this.pageHeightMax;
    this.pageRollup = false;
  }

  public toggleShow() {
    this.pageShow = !this.pageShow
  }

}
