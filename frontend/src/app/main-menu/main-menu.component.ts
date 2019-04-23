import { Component, OnInit } from '@angular/core';


@Component({
  selector: 'vdi-main-menu',
  templateUrl: './main-menu.component.html',
  styleUrls: ['./main-menu.component.scss']
})


export class MainMenuComponent implements OnInit {

  public listMenu: object[] = [ { name: 'Серверы', icon:'server', route:'page/nodes' },
                                { name: 'Ресурсы', icon:'database', route:'resourses', nested: [{ name:'Шаблоны ВМ', icon:'layer-group' }]},
                                { name: 'Пулы', icon:'desktop', route:'pools' }
                              ];

  constructor() {}

  ngOnInit() {
  }

}