import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { AppRoutingModule } from '@app/app-routing.module';
import { EventsModule } from '@pages/log/events/events.module';
import { FooterComponent } from './components/footer/footer.component';
import { HeaderUserComponent } from './components/header-user/header-user.component';
import { MainMenuComponent } from './components/main-menu/main-menu.component';
import { WaitComponent } from './components/wait/wait.component';
import { TasksModule } from '@app/pages/log/tasks/tasks.module';

@NgModule({
  declarations: [
    WaitComponent,
    MainMenuComponent,
    FooterComponent,
    HeaderUserComponent],
  imports: [
    CommonModule,     
    FontAwesomeModule,
    AppRoutingModule,
    EventsModule,
    TasksModule
  ],
  exports: [
    WaitComponent,
    MainMenuComponent,
    FooterComponent,
    HeaderUserComponent,
  ]

})
export class CoreModule {}
