import { ErrorsService } from './errors.service';
import { Component } from '@angular/core';
import { Subscription } from 'rxjs';

import {
	trigger,
	style,
	transition,
	animate
} from '@angular/animations';


@Component({
  selector: 'vdi-errors',
  templateUrl: './errors.component.html',
  styleUrls: ['./errors.component.scss'],
  animations: [
    trigger("animForm", [
      transition(":enter", [
        style({ opacity: 0 }),
        animate("150ms", style({ opacity: 1 }))
      ]),
      transition(":leave", [
        style({ opacity: 1 }),
        animate("150ms", style({ opacity: 0 }))
      ])
    ])
  ]
})
export class ErrorsComponent  {

  public errors = [];
  private timers: any[] = [];
  private errorsSub:Subscription;

  constructor(private service: ErrorsService) {}

  ngOnInit() {
    this.errorsSub = this.service.getErrors().subscribe((errors: object[]) => {
      errors.forEach((item: {}) => {
        this.errors.unshift(item);
        this.hideMessage();
      });
    });
  }

  private hideMessage(): void {
    if(this.errors.length) {
      let timeFunc = setTimeout(() => {
        this.errors.pop();
        this.timers.pop();
      },8000);
      this.timers.unshift(timeFunc);
    }
  }

  public closeMessage(id): void {
    this.errors.splice(id, 1);
    clearTimeout(this.timers[id]);
    this.timers.splice(id,1);
  }

  ngOnDestroy() {
    this.errorsSub.unsubscribe();
  }

}
