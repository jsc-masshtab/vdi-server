import { AuthStorageService } from './authStorage.service';
import { Injectable } from '@angular/core';
import {
  CanActivate,
  CanActivateChild
} from '@angular/router';


@Injectable({
  providedIn: 'root',
})

export class LoginGuard implements CanActivate, CanActivateChild {
  constructor(private authStorageService: AuthStorageService) {}

  public canActivate(): boolean {
    return this.authStorageService.checkLogin();
  }

  public canActivateChild(): boolean {
    return this.authStorageService.checkLogin();
  }

}
