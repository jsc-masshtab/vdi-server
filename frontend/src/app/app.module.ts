import { AuthStorageService } from './pages/login/authStorage.service';
import { DashboardModule } from './pages/dashboard/dashboard.module';
import { LoginModule } from './pages/login/login.module';
import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { ErrorsModule } from './core/components/errors/errors.module';
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
          faChevronCircleLeft, faChevronCircleRight, faAddressCard, faCheck, faUsersCog, faCrown, faColumns, faUpload, faIdCard, faSuitcase,
          faRss,
          faExpand,
          faGavel,
          faUndo,
          faPowerOff,
          faFire,
          faSearch,
          faFolder,
          faLaptop,
          faCircle,
          faExchangeAlt,
          faClone,
          faFileArchive,
          faBars,
          faWindowRestore,
          faLeaf,
          faShareAlt,
          faTerminal,
          faCommentDots,
          faWrench
        } from '@fortawesome/free-solid-svg-icons';
import { AuthInterceptor } from './pages/login/auth.Interceptor.http';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
/*  -----------------------------------   icons   --------------------------------------*/




@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    FontAwesomeModule,
    ApolloModule,
    HttpLinkModule,
    HttpClientModule,
    LoginModule,
    DashboardModule,
    ErrorsModule,
  ],
  bootstrap: [AppComponent],
  providers: [
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true,
      deps: [AuthStorageService]
    }
  ]
})


export class AppModule {
  constructor() {
    library.add(faDesktop, faDatabase, faLayerGroup, faPlusCircle, faMinusCircle, faSpinner, faServer, faCog, faChevronUp, faTimesCircle,
      faFolderOpen, faStar, faTv, faSyncAlt, faBuilding, faTrashAlt, faUsers, faMeh, faChartBar, faUser,
      faStopCircle, faPlayCircle, faPauseCircle, faEdit, faQuestionCircle, faCheckSquare, faExclamationTriangle, faHeartbeat,
      faChevronCircleUp, faComment, faClipboardList, faNewspaper, faUserCircle, faSignOutAlt, faChevronCircleLeft, faChevronCircleRight,
      faAddressCard, faCheck, faUsersCog, faCrown, faColumns, faUpload, faIdCard, faSuitcase, faRss, faExpand, faGavel, faStopCircle,
      faUndo, faPowerOff, faFire, faSearch, faFolder, faLaptop, faCircle, faExchangeAlt, faClone, faFileArchive, faBars, faWindowRestore, faLeaf, faShareAlt,
      faTerminal, faCommentDots, faWrench);
    }
}
