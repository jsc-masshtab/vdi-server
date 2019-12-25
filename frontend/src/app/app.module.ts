import { DashboardModule } from './dashboard/dashboard.module';
import { LoginModule } from './login/login.module';
import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HttpClientModule } from '@angular/common/http';
import { ErrorsModule } from './errors/errors.module';
import { HttpLinkModule } from 'apollo-angular-link-http';
import { ApolloModule  } from 'apollo-angular';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';


/*  -----------------------------------   icons   --------------------------------------*/
import { library } from '@fortawesome/fontawesome-svg-core';
import {
          faDesktop, faDatabase, faBuilding, faLayerGroup, faPlusCircle, faSpinner, faServer, faCog, faChevronUp, faTimesCircle,
          faFolderOpen, faStar, faMinusCircle, faTv, faSyncAlt, faTrashAlt, faUsers, faMeh,
          faChartBar, faUser, faStopCircle, faPlayCircle, faPauseCircle, faEdit, faQuestionCircle, faCheckSquare,
          faExclamationTriangle, faHeartbeat, faChevronCircleUp, faComment, faClipboardList, faNewspaper, faUserCircle, faSignOutAlt,
          faChevronCircleLeft, faChevronCircleRight
        } from '@fortawesome/free-solid-svg-icons';
/*  -----------------------------------   icons   --------------------------------------*/




@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    ApolloModule,
    HttpLinkModule,
    HttpClientModule,
    LoginModule,
    DashboardModule,
    ErrorsModule,
  ],
  bootstrap: [AppComponent]
})


export class AppModule {
  constructor() {
    library.add(faDesktop, faDatabase, faLayerGroup, faPlusCircle, faMinusCircle, faSpinner, faServer, faCog, faChevronUp, faTimesCircle,
      faFolderOpen, faStar, faTv, faSyncAlt, faBuilding, faTrashAlt, faUsers, faMeh, faChartBar, faUser,
      faStopCircle, faPlayCircle, faPauseCircle, faEdit, faQuestionCircle, faCheckSquare, faExclamationTriangle, faHeartbeat,
      faChevronCircleUp, faComment, faClipboardList, faNewspaper, faUserCircle, faSignOutAlt, faChevronCircleLeft, faChevronCircleRight);
    }
}
