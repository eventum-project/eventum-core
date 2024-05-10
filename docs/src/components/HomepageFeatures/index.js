import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Define time distribution',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        Eventum offers various methods to define time distribution of events.
        From using cron expressions to combining probability distribution functions
        - make your own scenario.
      </>
    ),
  },
  {
    title: 'Design event template',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        With the power of <a href='https://jinja.palletsprojects.com/templates/'>Jinja</a>,
        it's easy to design event template that suits your case. Additionally,
        advanced functionality enables you to save states, use samples, and run
        subprocesses directly from templates - very handy, isn't it?
      </>
    ),
  },
  {
    title: 'Send events anywhere',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        You are free to choose where to send generated events.
        Print it to stdout, save it to a file or maybe send it to
        some endpoint - it's up to you.
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
