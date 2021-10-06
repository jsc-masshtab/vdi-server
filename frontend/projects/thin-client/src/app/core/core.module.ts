import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { AppRoutingModule } from '@app/app-routing.module';
import { HeaderUserComponent } from '@app/core/components/header-user/header-user.component';
import { MainMenuComponent } from '@app/core/components/main-menu/main-menu.component';
import { WaitComponent } from '@app/core/components/wait/wait.component';
import { EventsModule } from '@app/pages/log/events/events.module';



@NgModule({
  declarations: [
    WaitComponent,
    MainMenuComponent,
    HeaderUserComponent],
  imports: [
    CommonModule,     
    FontAwesomeModule,
    AppRoutingModule,
    EventsModule,
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
