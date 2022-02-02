import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';

import { LoginComponent } from './login/login.component';
import { LoginService } from '../core/services/login.service';
import { AuthRoutingModule } from './auth-routing.module';
import { SharedModule } from '@app/shared/shared.module';



@NgModule({
  declarations: [LoginComponent],
  providers: [LoginService],
  imports: [
    ReactiveFormsModule,
    SharedModule,
    CommonModule,
    AuthRoutingModule,
    MatCheckboxModule
  ]
})
export class AuthModule { }
