import { LoginRoutingModule } from './login-routing.module';

import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { LoginComponent } from './login.component';
import { LoginService } from './login.service';



@NgModule({
  declarations: [
    LoginComponent
  ],
  providers: [LoginService],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    LoginRoutingModule
  ]
})


export class LoginModule {}
