import { Component, OnInit } from '@angular/core';


@Component({
  selector: 'vdi-main-menu',
  templateUrl: './main-menu.component.html',
  styleUrls: ['./main-menu.component.scss']
})


export class MainMenuComponent implements OnInit {

  public listMenu: object[] = [ { name: 'Настройки', icon:'cog', route:'settings/servers',
                                        nested: [{ name: 'Серверы', icon:'server',route:'settings/servers' }] },

                                { name: 'Ресурсы', icon: 'database', route:'resourses/clusters',
                                        nested: [{ name: 'Кластеры', icon:'building', route:'resourses/clusters',
                                                          nested: [{ name: 'Серверы', icon:'server', route:'resourses/clusters/nodes' }] 
                                                }]               
                                },

                                { name: 'Пулы', icon:'desktop', route:'pools' }
                              ];

  constructor() {}

  ngOnInit() {
  }

}