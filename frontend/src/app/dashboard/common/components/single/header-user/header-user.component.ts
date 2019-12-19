import { AuthStorageService } from './../../../../../login/authStorage.service';

import { Component, OnDestroy, OnInit } from '@angular/core';

import {
  trigger,
  style,
  transition,
  animate
} from '@angular/animations';


@Component({
  selector: 'vdi-header-user',
  templateUrl: './header-user.component.html',
  styleUrls: ['./header-user.scss'],
  animations: [
    trigger('animForm', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('150ms', style({ opacity: 1 }))
      ]),
      transition(':leave', [
        style({ opacity: 1 }),
        animate('150ms', style({ opacity: 0 }))
      ])
    ])
  ]
})
export class HeaderUserComponent implements OnInit, OnDestroy {

  public user: string;
  public openMenu: boolean = false;

  constructor(private authStorageService: AuthStorageService) {}

  ngOnInit() {
    this.user = this.authStorageService.getItemStorage('username');
  }

  public open() {
    this.openMenu = !this.openMenu;
  }

}
