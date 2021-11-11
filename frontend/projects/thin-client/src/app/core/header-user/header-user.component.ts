import { Component, OnInit } from '@angular/core';

import { AuthStorageService } from '../services/authStorage.service';
import { LoginService } from '../services/login.service';






@Component({
  selector: 'tc-header-user',
  templateUrl: './header-user.component.html',
  styleUrls: ['./header-user.scss']
})
export class HeaderUserComponent implements OnInit {

  public user: string;
  public openMenu: boolean = false;

  constructor(private authStorageService: AuthStorageService, private loginService: LoginService) {}

  ngOnInit() {
    this.user = this.authStorageService.getItemStorage('username');
  }

  public open(): void {
    this.openMenu = !this.openMenu;
  }

  public logout(): void {
    this.loginService.logout().subscribe(() => {
      this.authStorageService.logout();
    });
  }

}
