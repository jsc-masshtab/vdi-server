import { Component, OnInit,  ChangeDetectionStrategy,ChangeDetectorRef } from '@angular/core';
import { trigger, style, animate, transition } from "@angular/animations";
import { Router, NavigationStart} from '@angular/router';

@Component({
  selector: 'vdi-main-menu',
  templateUrl: './main-menu.component.html',
  styleUrls: ['./main-menu.component.scss'],
  //changeDetection: ChangeDetectionStrategy.OnPush,
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
                                { name: 'Пулы', icon:'desktop', route:'pools'},

                                { name: 'Ресурсы', icon: 'database', route:'resourses/clusters',open: false,
                                        nested: [ { name: 'Кластеры', icon:'building', route:'resourses/clusters'},
                                                  { name: 'Серверы', icon:'server', route:'resourses/nodes' },
                                                  { name: 'Пулы данных', icon:'folder-open', route:'resourses/datapools' }]               
                                },
                                { name: 'Настройки', icon:'cog', route:'settings/controllers', open: false,
                                        nested: [{ name: 'Контроллеры', icon:'server',icon_dependent:'certificate',route:'settings/controllers' }] 
                                }
                              ];

  constructor(private router: Router) {}

  ngOnInit() {
    this.openRouteInit();
  }

  public check(item): boolean {
    let result: boolean;
    let clickItemRoute: string;
    let url: string;

    if(item.nested) {
      clickItemRoute = item.nested[0].route.split('/')[0];
      url = this.router.url.split('/')[1];
      clickItemRoute === url ? result = true : result = false;
    } else {
      clickItemRoute = item.route.split('/')[0];
      url = this.router.url.split('/')[1];
      clickItemRoute === url ? result = true : result = false;
    }
    return result;
  }


  public clickItem(index,listMenu,event) {
    event.stopPropagation();
    listMenu[index].open = !listMenu[index].open;
  }


  private openRouteInit() {
   this.router.events.subscribe((event) => {
      if(event instanceof NavigationStart) {
        let url = event.url.split('/',2)[1]; // url в строке браузера 1 крошка после домена
        this.listMenu.forEach((element,index) => {
          let route = element['route'].split('/',1).join();
          if(route === url && element['nested']) {
            if(!this.listMenu[index]['open']) {
              this.listMenu[index]['open'] = true;    
            }
          }
        });
      }
    });
  }
  

}