import { AuthStorageService } from './authStorage.service';
import { Injectable } from '@angular/core';
import {
  CanActivate, Router,
  ActivatedRouteSnapshot,
  RouterStateSnapshot,
  CanActivateChild
} from '@angular/router';


@Injectable({
  providedIn: 'root',
})

export class LoginGuard implements CanActivate, CanActivateChild {
  constructor(private authService: AuthStorageService, private router: Router) {}

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
    let url: string = state.url;

    console.log(url, route, 'canActivate');

    return this.checkLogin(url);
  }

  canActivateChild(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
    return this.canActivate(route, state);
  }

  // canLoad(route: Route): boolean {
  //   let url = `/${route.path}`;

  //   return this.checkLogin(url);
  // }

  checkLogin(url: string): boolean {
    console.log(this.authService.isLoggedIn,'this.authService.isLoggedIn',url);
    

    // setTimeout(() => {
    //   this.authService.isLoggedIn = false;
    //   console.log('this.authService.isLoggedIn = false', this.authService.isLoggedIn);
    // }, 10000);

    if (this.authService.isLoggedIn) { return true; }

    // Store the attempted URL for redirecting
    // this.authService.redirectUrl = url;



    // Navigate to the login page with extras
    this.router.navigate(['/login']);
    return false;
  }
}
