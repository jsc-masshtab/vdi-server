
import { BrowserModule } from '@angular/platform-browser';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import { NgModule } from '@angular/core';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { GraphQLModule } from './graphql.module';
import { HttpClientModule } from '@angular/common/http';



/*  -----------------------------------   icons   --------------------------------------*/
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core'
import { faDesktop,faDatabase, faLayerGroup,faPlusCircle } from '@fortawesome/free-solid-svg-icons';
/*  -----------------------------------   icons   --------------------------------------*/


import { MainMenuComponent } from './main-menu/main-menu.component';
import { TeplatesService } from './templates/templates.service';
import { TemplatesComponent } from './templates/templates.component';

import { PollsComponent } from './polls/polls.component';
import { TableComponentComponent } from './common/table-component/table-component.component';
import { BreadcrumbsComponent } from './common/breadcrumbs/breadcrumbs.component';
import { PoolAddComponent } from './polls/pool-add/pool-add.component';
import { PoolsService } from './polls/polls.service';


/*  -----------------------------------   material   --------------------------------------*/
import { MAT_DIALOG_DEFAULT_OPTIONS } from '@angular/material';
import { MatDialogModule } from '@angular/material/dialog';
/*  -----------------------------------   material   --------------------------------------*/



@NgModule({
  declarations: [
    AppComponent,
    MainMenuComponent,
    TemplatesComponent,
    TableComponentComponent,
    PollsComponent,
    BreadcrumbsComponent,
    PoolAddComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    GraphQLModule,
    HttpClientModule,
    FontAwesomeModule,
    MatDialogModule
  ],
  entryComponents: [
    PoolAddComponent
  ],
  providers: 
            [
              TeplatesService,
              PoolsService,
              { provide: MAT_DIALOG_DEFAULT_OPTIONS, useValue: { hasBackdrop: true, restoreFocus: true } }
            ],
  bootstrap: [AppComponent]
})


export class AppModule {
  constructor() { 
    library.add(faDesktop,faDatabase,faLayerGroup,faPlusCircle
      ); // Неиспользуемые иконки при финальной сборке удаляются
  }


}
