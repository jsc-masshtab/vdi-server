import { trigger, style, animate, transition } from '@angular/animations';
import { Component } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Router, NavigationEnd } from '@angular/router';

import { environment } from 'environments/environment';

@Component({
  selector: 'vdi-main-menu',
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
  public toggleStatistics: boolean = false;
  public multiple: boolean = false;

  public clickedManage: string = '';

  constructor(private router: Router, private dialog: MatDialog) {
    this.multiple = environment.multiple || false;
    this.beginRoute();
  }

  private beginRoute() {
    this.router.events.subscribe((event) => {
        if (event instanceof NavigationEnd) {

          if (this.dialog.openDialogs.length) {
            this.dialog.closeAll();
          }

          let clickedManage1 = event.urlAfterRedirects.split('/')[2] || null;
          let clickedManage2 = event.urlAfterRedirects.split('/')[3] || null;

          if (clickedManage1) {

            if (clickedManage1 === 'controllers') {
              this.clickedManage = 'controllers';
              return;
            }

            if (clickedManage1 === 'pools') {
              this.clickedManage = 'pools';
              return;
            }

            if (clickedManage1 === 'resourses') {
              this.toggleResourse = true;
            }

            if (clickedManage1 === 'clients') {
              this.toggleThin = true;
            }

            if (clickedManage1 === 'settings') {
              this.toggleSetting = true;
            }

            if (clickedManage1 === 'log') {
              this.toggleLog = true;
            }

            if (clickedManage1 === 'statistics') {
              this.toggleStatistics = true;
            }
          }

          if (clickedManage2) {
            this.clickedManage = clickedManage2;
          }
        }
      });
  }

  public resourseToggle(): void {
    this.toggleResourse = !this.toggleResourse;
  }

  public thinToggle(): void {
    this.toggleThin = !this.toggleThin;
  }

  public settingToggle(): void {
    this.toggleSetting = !this.toggleSetting;
  }

  public logToggle(): void {
    this.toggleLog = !this.toggleLog;
  }

  public statisticsToggle(): void {
    this.toggleStatistics = !this.toggleStatistics;
  }

  public routeTo(route: string) {
    setTimeout(() => {
      this.router.navigate(['pages/' + route]);
    }, 0);
  }
}
