import { Component, OnInit } from '@angular/core';

import { AuthStorageService } from '../../core/services/authStorage.service';
import { LoginService } from '../../core/services/login.service';

@Component({
  selector: 'tc-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {

  public user: string | null;
  constructor( private authStorageService: AuthStorageService, private loginService: LoginService) { }

  ngOnInit() {
  }

  public logout(): void {
    this.loginService.logout().subscribe(() => {
      this.authStorageService.logout();
    
    });
  }
}
