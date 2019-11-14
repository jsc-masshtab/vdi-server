
import { HostListener, ElementRef } from '@angular/core';

export class DetailsMove  {

    public pageHeightMinNumber: number = 315;
    public pageHeightMin: string = '315px';
    public pageHeightMax: string = '100%';
    public pageHeight: string = '100%';
    public pageRollup: boolean = false;
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
    setTimeout(() => {
      this.pageHeight = this.pageHeightMin;

      if ((view.nativeElement.clientHeight - this.pageHeightMinNumber) < (this.pageHeightMinNumber + 250)) {
        this.pageRollup = true;
      }
    }, 0);
  }

  public componentDeactivate(): void {
    setTimeout(() => {
      this.pageHeight = this.pageHeightMax;
      this.pageRollup = false;
    }, 0);
  }

}
