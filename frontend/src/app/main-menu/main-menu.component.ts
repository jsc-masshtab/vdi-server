import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'vdi-main-menu',
  templateUrl: './main-menu.component.html',
  styleUrls: ['./main-menu.component.scss']
})
export class MainMenuComponent implements OnInit {

  public listMenu: object[] = [{name:'Ресурсы',icon:'database'},{name:'Пулы',icon:'desktop'}];

  constructor() { }

  ngOnInit() {
  }

}
