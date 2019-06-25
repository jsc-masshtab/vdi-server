import { Component, OnInit } from '@angular/core';
import { trigger, style, animate, transition } from "@angular/animations";
import { Router, NavigationEnd} from '@angular/router';

@Component({
  selector: 'vdi-main-menu',
  templateUrl: './main-menu.component.html',
  styleUrls: ['./main-menu.component.scss'],
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [   // :enter is alias to 'void => *'
        style({opacity:0}),
        animate(250, style({opacity:1})) 
      ]),
      transition(':leave', [   // :leave is alias to '* => void'
        animate(0, style({opacity:0})) 
      ])
    ]) ]
})


export class MainMenuComponent implements OnInit {

  public toggleResourse:boolean = false;
  public toggleSetting:boolean = false;
  public clickedManage: string = '';

  constructor(private router: Router) {}

  ngOnInit() {
    this.beginRoute();
  }

  private beginRoute() {

		this.router.events.subscribe((event) => {
			if(event instanceof NavigationEnd) {

        let clickedManage1 = event.urlAfterRedirects.split('/')[1] || null;
        let clickedManage2 = event.urlAfterRedirects.split('/')[2] || null;

        if(clickedManage1) {
          if(clickedManage1 === 'resourses') {
						this.toggleResourse = true;
					}
					if(clickedManage1 === 'settings') {
						this.toggleSetting = true;
          }

          if(clickedManage1 === 'pools') {
            this.clickedManage = 'pools';
            return;
          }
        }
       
        if(clickedManage2) {
          this.clickedManage = clickedManage2;
        }
      }
    });
  }

  public resourseToggle(): void {
		this.toggleResourse = !this.toggleResourse;
	}

	public settingToggle(): void {
		this.toggleSetting = !this.toggleSetting;
  }
  
  public routeTo(route: string) {
		setTimeout(() => {
			this.router.navigate([route]);
		}, 0);
	}
  

}