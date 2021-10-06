import { trigger, style, animate, transition } from '@angular/animations';
import { Component } from '@angular/core';
import { Router} from '@angular/router';

@Component({
  selector: 'app-main-menu',
  templateUrl: './main-menu.component.html',
  styleUrls: ['./main-menu.component.scss'],
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [   // :enter is alias to 'void => *'
        style({opacity: 0}),
        animate(250, style({opacity: 1}))
      ]),
      transition(':leave', [   // :leave is alias to '* => void'
        animate(0, style({opacity: 0}))
      ])
    ]) ]
})


export class MainMenuComponent {

  public toggleResourse: boolean = false;
  public toggleThin: boolean = false;
  public toggleSetting: boolean = false;
  public toggleLog: boolean = false;

  public clickedManage: string = '';

  constructor(private router: Router, ) { }


  public routeTo(route: string) {
    setTimeout(() => {
      this.router.navigate(['pages/' + route]);
    }, 0);
  }
}
