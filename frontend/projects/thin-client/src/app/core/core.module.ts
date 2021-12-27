import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { HeaderUserComponent } from './header-user/header-user.component';
import { WaitComponent } from './wait/wait.component';
import { MainMenuComponent } from './main-menu/main-menu.component';
import { AppRoutingModule } from '../app-routing.module';
import { GenerateQrcodeComponent } from '../components/generate-qrcode/generate-qrcode.component';
import { ReactiveFormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialogModule } from '@angular/material/dialog';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { NgxQRCodeModule } from '@techiediaries/ngx-qrcode';





@NgModule({
  declarations: [
    WaitComponent,
    MainMenuComponent,
    HeaderUserComponent,
    GenerateQrcodeComponent
  ],
  imports: [
    CommonModule,     
    FontAwesomeModule,
    AppRoutingModule,
    CommonModule,
    FontAwesomeModule,
    AppRoutingModule,
    MatDialogModule,
    MatSelectModule,
    ReactiveFormsModule,
    MatCheckboxModule,
    MatInputModule,
    NgxQRCodeModule
  ],
  providers: [],
  exports: [
    WaitComponent,
    MainMenuComponent,
    HeaderUserComponent,
  ]

})
export class CoreModule {

}
