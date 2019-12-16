import { AuthStorageService } from './authStorage.service';
import {
  trigger,
  style,
  transition,
  animate
} from '@angular/animations';
import { FormBuilder, FormGroup } from '@angular/forms';

import { Component, OnInit } from '@angular/core';
import { LoginService } from './login.service';
// import { Router } from '@angular/router';


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

  constructor(private fb: FormBuilder, private authService: AuthStorageService, private loginService: LoginService) {
    this.createForm();
  }

  ngOnInit() {
    this.loaded = true;
  }

  private createForm(): void {
    this.loginForm = this.fb.group({
      username: '' ,
      password: ''
    });
  }

  public send() {
    console.log(this.loginForm.value, this.authService);
    this.loginService.auth(this.loginForm.value).subscribe((res) => console.log(res));
  }
}
