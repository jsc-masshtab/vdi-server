import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { GraphQLModule } from './graphql.module';
import { HttpClientModule } from '@angular/common/http';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { library } from '@fortawesome/fontawesome-svg-core'
import { faDesktop,faDatabase } from '@fortawesome/free-solid-svg-icons';
import { MainMenuComponent } from './main-menu/main-menu.component';
import { TeplatesService } from './templates/templates.service';
import { TemplatesComponent } from './templates/templates.component';


@NgModule({
  declarations: [
    AppComponent,
    MainMenuComponent,
    TemplatesComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    GraphQLModule,
    HttpClientModule,
    FontAwesomeModule

  ],
  providers: [TeplatesService],
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
