import { Component, OnInit, OnChanges } from '@angular/core';


@Component({
  selector: 'vdi-main-menu',
  templateUrl: './main-menu.component.html',
  styleUrls: ['./main-menu.component.scss']
})


export class MainMenuComponent implements OnInit, OnChanges {

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

  constructor() {}

  ngOnInit() {
  }

  ngOnChanges(a) {
    console.log(a,'kdkkd');
  }

  public clickItem(index,listMenu) {
    let i = index;
    listMenu[i].open = !listMenu[i].open;

    listMenu.forEach((element,index) => {
      if(index != i) {
        if(element.open) {
          element.open = false;
        }
      }
    });
  }
  

}