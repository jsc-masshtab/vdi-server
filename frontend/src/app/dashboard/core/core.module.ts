import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSelectModule } from '@angular/material/select';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { AppRoutingModule } from 'src/app/app-routing.module';
import { EventsModule } from '../pages/log/events/events.module';
import { FooterComponent } from './components/footer/footer.component';
import { HeaderUserComponent } from './components/header-user/header-user.component';
import { MainMenuComponent } from './components/main-menu/main-menu.component';
import { WaitComponent } from './components/wait/wait.component';





@NgModule({
  declarations: [
    WaitComponent,
    MainMenuComponent,
    FooterComponent,
    HeaderUserComponent],
  imports: [     
    CommonModule,
    FontAwesomeModule,
    MatDialogModule,
    ReactiveFormsModule,
    MatCheckboxModule,
    MatSelectModule,
    AppRoutingModule,
    FormsModule,
    EventsModule,
  ],
  providers: [],
  exports: [
    WaitComponent,
    MainMenuComponent,
    FooterComponent,
    HeaderUserComponent,
  ]

})
export class CoreModule {

}
