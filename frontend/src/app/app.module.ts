import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
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
          faWrench,
          faSlidersH,
          faClock,
          faCogs,
          faEnvelope,
          faEraser,
          faDownload
} from '@fortawesome/free-solid-svg-icons';

import { ApolloModule  } from 'apollo-angular';
import { HttpLinkModule } from 'apollo-angular-link-http';

import { ErrorsModule } from '@core/components/errors/errors.module';

import { DashboardModule } from '@pages/dashboard/dashboard.module';
import { AuthInterceptor } from '@pages/login/auth.Interceptor.http';
import { AuthStorageService } from '@pages/login/authStorage.service';
import { LoginModule } from '@pages/login/login.module';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

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
    library.add(faDesktop, faDatabase, faLayerGroup, faPlusCircle, faMinusCircle, faSpinner, faServer, faCog, faCogs, faChevronUp, faTimesCircle,
      faFolderOpen, faStar, faTv, faSyncAlt, faBuilding, faTrashAlt, faUsers, faMeh, faChartBar, faUser,
      faStopCircle, faPlayCircle, faPauseCircle, faEdit, faQuestionCircle, faCheckSquare, faExclamationTriangle, faHeartbeat,
      faChevronCircleUp, faComment, faClipboardList, faNewspaper, faUserCircle, faSignOutAlt, faChevronCircleLeft, faChevronCircleRight,
      faAddressCard, faCheck, faUsersCog, faCrown, faColumns, faUpload, faIdCard, faSuitcase, faRss, faExpand, faGavel, faStopCircle,
      faUndo, faPowerOff, faFire, faSearch, faFolder, faLaptop, faCircle, faSlidersH, faExchangeAlt, faClone, faFileArchive, faBars, faWindowRestore, faLeaf, faShareAlt,
      faTerminal, faCommentDots, faWrench, faClock, faEnvelope, faEraser, faDownload);
    }
}
