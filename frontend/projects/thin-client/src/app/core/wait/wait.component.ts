import {
  trigger,
  style,
  transition,
  animate
} from '@angular/animations';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subscription } from 'rxjs';

import { WaitService } from './wait.service';


@Component({
  selector: 'tc-wait',
  templateUrl: './wait.component.html',
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
  ]
})
export class WaitComponent implements OnInit, OnDestroy {

  private waitSub: Subscription;
  public wait: boolean | undefined;

  constructor(private service: WaitService) {}

  ngOnInit() {
    this.waitSub = this.service.getWait().subscribe((wait: boolean) => {
      setTimeout(() => {
        this.wait = wait;
      })
    });
  }

  ngOnDestroy() {
    this.waitSub.unsubscribe();
  }
}
