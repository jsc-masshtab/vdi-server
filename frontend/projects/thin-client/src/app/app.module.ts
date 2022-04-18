import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import {
  faBars,
  faChartBar,
  faCheckSquare,
  faCog,
  faCommentDots,
  faDesktop, 
  faExclamationTriangle, 
  faFire, 
  faPauseCircle, 
  faPlay, faPlayCircle, faPowerOff, faSignOutAlt, faSpinner, faStopCircle, faSyncAlt, faTimesCircle, faTv, faUndo, faUserCircle, faEdit, faHeartbeat} from '@fortawesome/free-solid-svg-icons';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { AuthStorageService } from './core/services/authStorage.service';
import { AuthInterceptor } from './core/services/auth.Interceptor.http';
import { AuthModule } from './auth/auth.module';
import { DashboardModule } from './pages/dashboard/dashboard.module';
import { ErrorsModule } from './core/errors/errors.module';
import { ErrorsService } from './core/errors/errors.service';
import { CoreModule } from './core/core.module';
import { FaIconLibrary } from '@fortawesome/angular-fontawesome';


@NgModule({
  declarations: [	
    AppComponent,
   ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    CoreModule,
    ReactiveFormsModule,
    HttpClientModule,
    AppRoutingModule,
    AuthModule,
    DashboardModule,
    ErrorsModule
  ],
  providers: [
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true,
      deps: [AuthStorageService, ErrorsService]
    }
  ],
  bootstrap: [AppComponent]
})
export class AppModule {
  constructor(library: FaIconLibrary) {
    library.addIcons(
      faCommentDots,
      faPlay, 
      faUserCircle, 
      faSignOutAlt, 
      faCog, 
      faDesktop, 
      faSyncAlt, 
      faTv, 
      faChartBar, 
      faTimesCircle, 
      faSpinner, 
      faBars, 
      faCheckSquare, 
      faTimesCircle, 
      faPlayCircle, 
      faPauseCircle, 
      faStopCircle, 
      faUndo, 
      faExclamationTriangle,
      faFire,
      faPowerOff,
      faEdit,
      faHeartbeat
      )
  }
 }
