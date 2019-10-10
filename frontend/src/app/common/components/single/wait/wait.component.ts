import { WaitService } from './wait.service';
import { Component } from '@angular/core';
import { Subscription } from 'rxjs';

import {
	trigger,
	style,
	transition,
	animate
} from '@angular/animations';


@Component({
  selector: 'vdi-wait',
  templateUrl: './wait.component.html',
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
export class WaitComponent  {

  private waitSub:Subscription;
  public wait:boolean = false;

  constructor(private service: WaitService) {}

  ngOnInit() {
    this.waitSub = this.service.getWait().subscribe((wait:boolean) => {
      this.wait = wait;
    });
  }

  ngOnDestroy() {
    this.waitSub.unsubscribe();
  }

}
