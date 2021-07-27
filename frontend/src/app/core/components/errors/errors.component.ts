import {
  trigger,
  style,
  transition,
  animate
} from '@angular/animations';
import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';

import { ErrorsService } from './errors.service';



interface IError {
  message: string;
}

@Component({
  selector: 'vdi-errors',
  templateUrl: './errors.component.html',
  styleUrls: ['./errors.component.scss'],
  animations: [
    trigger('animForm', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('150ms', style({ opacity: 1 }))
      ]),
      transition(':leave', [
        style({ opacity: 1 }),
        animate('150ms', style({ opacity: 0 }))
      ])
    ])
  ],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ErrorsComponent  implements OnInit, OnDestroy {

  public errors = [];
  private timers: any[] = [];
  private errorsSub: Subscription;

  constructor(private service: ErrorsService, private cdr: ChangeDetectorRef) {}

  ngOnInit() {
    this.errorsSub = this.service.getErrors().pipe(filter(value => Array.isArray(value) || typeof value === 'string'))
    .subscribe((errors: IError[] | string) => {
      if (Array.isArray(errors)) {
        errors.forEach((item: {}) => {
          this.addError(item);
        });
      } else {
        this.addError(errors);
      }
      this.cdr.detectChanges();
    });
  }

  private addError(item): void {
    this.errors.unshift(item);
    this.hideMessage();
  }

  private hideMessage(): void {
    if (this.errors.length) {
      const timeFunc = setTimeout(() => {
        this.errors.pop();
        this.timers.pop();
        this.cdr.detectChanges();
      }, 8000);
      this.timers.unshift(timeFunc);
    }
  }

  public closeMessage(id): void {
    this.errors.splice(id, 1);
    clearTimeout(this.timers[id]);
    this.timers.splice(id, 1);
  }

  ngOnDestroy() {
    this.errorsSub.unsubscribe();
  }

}
