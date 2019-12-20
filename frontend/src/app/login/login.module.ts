import { LoginRoutingModule } from './login-routing.module';

import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { LoginComponent } from './login.component';
import { LoginService } from './login.service';
import { MatCheckboxModule } from '@angular/material';



@NgModule({
  declarations: [
    LoginComponent
  ],
  providers: [LoginService],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    LoginRoutingModule,
    MatCheckboxModule
  ]
})


export class LoginModule {}
