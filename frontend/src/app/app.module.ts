import { PoolsService } from './polls/polls.service';
import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { GraphQLModule } from './graphql.module';
import { HttpClientModule } from '@angular/common/http';



/*  -----------------------------------   icons   --------------------------------------*/
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core'
import { faDesktop,faDatabase } from '@fortawesome/free-solid-svg-icons';
/*  -----------------------------------   icons   --------------------------------------*/


import { MainMenuComponent } from './main-menu/main-menu.component';
import { TeplatesService } from './templates/templates.service';
import { TemplatesComponent } from './templates/templates.component';

import { PollsComponent } from './polls/polls.component';
import { TableComponentComponent } from './common/table-component/table-component.component';
import { BreadcrumbsComponent } from './common/breadcrumbs/breadcrumbs.component';


@NgModule({
  declarations: [
    AppComponent,
    MainMenuComponent,
    TemplatesComponent,
    TableComponentComponent,
    PollsComponent,
    BreadcrumbsComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    GraphQLModule,
    HttpClientModule,
    FontAwesomeModule

  ],
  providers: [TeplatesService, PoolsService],
  bootstrap: [AppComponent]
})
export class AppModule {
  constructor() { 
    library.add(faDesktop,faDatabase); // Неиспользуемые иконки при финальной сборке удаляются
  }


 }


// link?: ApolloLink;
//     cache: ApolloCache<TCacheShape>;
//     ssrForceFetchDelay?: number;
//     ssrMode?: boolean;
//     connectToDevTools?: boolean;
//     queryDeduplication?: boolean;
//     defaultOptions?: DefaultOptions;
//     resolvers?: Resolvers | Resolvers[];
//     typeDefs?: string | string[] | DocumentNode | DocumentNode[];
//     fragmentMatcher?: FragmentMatcher;
//     name?: string;
//     version?: string;
