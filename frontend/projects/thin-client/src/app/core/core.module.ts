import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { HeaderUserComponent } from './header-user/header-user.component';
import { WaitComponent } from './wait/wait.component';
import { MainMenuComponent } from './main-menu/main-menu.component';
import { AppRoutingModule } from '../app-routing.module';





@NgModule({
  declarations: [
    WaitComponent,
    MainMenuComponent,
    HeaderUserComponent],
  imports: [
    CommonModule,     
    FontAwesomeModule,
    AppRoutingModule,
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
