/* tslint:disable:directive-class-suffix */
/* eslint-disable @angular-eslint/directive-class-suffix */
import { HostListener, ElementRef, Directive, ViewChild } from '@angular/core';

@Directive()
export class DetailsMove  {

  public pageHeightMinNumber: number = 315;
  public pageHeightMin: string = 'auto';
  public pageHeightMax: string = '100%';
  public pageHeight: string = '100%';
  public pageRollup: boolean = false;
  public pageShow: boolean = false
  public timeout: any;

  constructor() { }
  
  @ViewChild('view', { static: true }) view: ElementRef;

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

  public componentActivate(view = this.view): void {

    const listVeiw = view.nativeElement.childNodes[0];
    listVeiw.style.maxHeight = "310px";

    this.pageHeight = this.pageHeightMin;

    if ((view.nativeElement.clientHeight - this.pageHeightMinNumber) < (this.pageHeightMinNumber + 250)) {
      this.pageRollup = true;
    }
  }

  public componentDeactivate(): void {
    const listVeiw = this.view.nativeElement.childNodes[0];
    listVeiw.style.maxHeight = "unset";

    this.pageHeight = this.pageHeightMax;
    this.pageRollup = false;
  }

  public toggleShow() {
    this.pageShow = !this.pageShow
  }

}
