
import { Component, ViewEncapsulation, AfterViewInit } from '@angular/core';


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  encapsulation: ViewEncapsulation.None
})

export class AppComponent implements AfterViewInit {

  private _element: HTMLElement;

  constructor() {}

  public ngAfterViewInit(): void {
    this._element = document.getElementById('preloader');
    this._element.style['display'] = 'none';
  }

}
