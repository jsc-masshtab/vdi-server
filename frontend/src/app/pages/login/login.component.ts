import {
  trigger,
  style,
  transition,
  animate
} from '@angular/animations';

import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormControl, FormGroup } from '@angular/forms';
import { Router } from '@angular/router';

import { ErrorsService } from '../../core/components/errors/errors.service';
import { AuthStorageService } from './authStorage.service';
import { LoginService } from './login.service';

@Component({
  selector: 'vdi-login',
  templateUrl: './login.html',
  styleUrls: ['./login.scss'],
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

export class LoginComponent implements OnInit {

  public loaded: boolean = false;
  public loginForm: FormGroup;
  public useCode = new FormControl(false)

  constructor(
    private fb: FormBuilder,
    private authStorageService: AuthStorageService,
    private loginService: LoginService,
    private route: Router,
    private errorService: ErrorsService
  ) {}

  ngOnInit() {
    this.createForm();
    this.checkLogin();

    this.useCode.valueChanges.subscribe((value) => {
      if(!value) {
        this.loginForm.get('code').setValue('');
      }
    })
  }

  private createForm(): void {
    this.loginForm = this.fb.group({
      username: '',
      password: '',
      code: '',
      ldap: false
    });
  }
  
  private checkLogin(): void {
    if (this.authStorageService.checkLogin()) {
      this.route.navigate(['/pages']);
    } else {
      this.getSettings();
    }
  }

  private getSettings(): void {
    this.loginService.getSettings().subscribe((res) => {

      this.loginForm.get('ldap').setValue(res.ldap);

      if(res.sso) {
        this.getSSO();
      } else {
        this.routePage();
      }
    })
  }

  routePage() {
    if (this.authStorageService.checkLogin()) {
      this.route.navigate(['/pages']);
    } else {
      this.loaded = true;
    }
  }

  private getSSO() {
    this.loginService.getSSO().subscribe(

      (res) => {
        this.authStorageService.saveInStorage(res.body.data);
        this.routePage();
      }, 

      (res) => {
        if(!res.status) {
          this.getSSO();
        } else {
          this.routePage();
        }
      }
    );
  }

  public auth() {
    this.loginService.auth(this.loginForm.value).subscribe((res) => {

      if (res && res.data) {
        this.authStorageService.saveInStorage(res.data);
        this.routePage();
      }

      if (res.errors !== undefined) {
        this.errorService.setError(res.errors);
        this.routePage();
      }
    });
  }
}
