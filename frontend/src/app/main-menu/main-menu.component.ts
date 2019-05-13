import { Component, OnInit } from '@angular/core';
import { trigger, state, style, animate, transition } from "@angular/animations";
import { Router, NavigationStart} from '@angular/router';


@Component({
  selector: 'vdi-main-menu',
  templateUrl: './main-menu.component.html',
  styleUrls: ['./main-menu.component.scss'],
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [   // :enter is alias to 'void => *'
        style({opacity:0}),
        animate(300, style({opacity:1})) 
      ]),
      transition(':leave', [   // :leave is alias to '* => void'
        animate(0, style({opacity:0})) 
      ])
    ]) ]
})


export class MainMenuComponent implements OnInit {

  public listMenu: object[] = [
                                { name: 'Пулы', icon:'desktop', route:'pools' },

                                { name: 'Ресурсы', icon: 'database', route:'resourses/clusters',open: false,
                                        nested: [{ name: 'Кластеры', icon:'building', route:'resourses/clusters',
                                                          nested: [{ name: 'Серверы', icon:'server', route:'resourses/clusters/nodes' }] 
                                                }]               
                                },
                                { name: 'Настройки', icon:'cog', route:'settings/servers', open: false,
                                        nested: [{ name: 'Серверы', icon:'server',route:'settings/servers' }] }
                              ];

  constructor(private router: Router) {}

  ngOnInit() {
    this.openRoute(); 
  }

  public clickItem(index,listMenu) {
    listMenu[index].open = !listMenu[index].open;
  }

  private openRoute() {
    this.router.events.subscribe((event) => {
			if(event instanceof NavigationStart) {
        let urlBegin = event.url.split('/',2);
        this.listMenu.forEach((element,index) => {
          var routeBegin = element['route'].split('/',1);
          if(routeBegin.join() === urlBegin[1]) {
            this.listMenu[index]['open'] = true;
          }
        });
			}
    });
  }
  

}