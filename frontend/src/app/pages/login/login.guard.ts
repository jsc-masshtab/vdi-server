import { Injectable } from '@angular/core';
import {
  CanActivate,
  CanActivateChild
} from '@angular/router';

import { AuthStorageService } from './authStorage.service';


@Injectable({
  providedIn: 'root',
})

export class LoginGuard implements CanActivate, CanActivateChild {
  constructor(private authStorageService: AuthStorageService) {}

  public canActivate(): boolean {
    console.log('route', navigator)
    return this.authStorageService.checkLogin();
  }

  public canActivateChild(): boolean {
    console.log('child-route', navigator)
    return this.authStorageService.checkLogin();
  }

}
