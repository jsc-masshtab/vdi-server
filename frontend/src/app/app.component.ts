import { Component, AfterViewInit } from '@angular/core';


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})

export class AppComponent implements AfterViewInit {

  private _element: HTMLElement;

  constructor() {}

  public ngAfterViewInit(): void {
    this._element = document.getElementById('preloader');
    this._element.style['display'] = 'none';
  }

}
